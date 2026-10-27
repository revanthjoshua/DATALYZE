"""Keep serverless HTTP envelopes bounded without truncating persisted datasets."""
from starlette.responses import JSONResponse


class PayloadLimitMiddleware:
    def __init__(self, app, max_request_bytes=None, max_response_bytes=None):
        self.app = app
        self.max_request_bytes = max_request_bytes
        self.max_response_bytes = max_response_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        original_receive = receive
        if self.max_request_bytes:
            headers = dict(scope.get("headers", []))
            try:
                declared = int(headers.get(b"content-length", b"0"))
                if declared < 0:
                    raise ValueError
            except ValueError:
                return await JSONResponse({"detail": "Invalid request size."}, status_code=400)(scope, receive, send)
            if declared > self.max_request_bytes:
                return await self.reject_request(scope, receive, send)
            # Check actual bytes too: chunked bodies or an incorrect Content-Length
            # must not enter a mutation handler before their size is established.
            chunks, size = [], 0
            while True:
                message = await original_receive()
                if message["type"] == "http.disconnect":
                    return
                body = message.get("body", b"")
                size += len(body)
                if size > self.max_request_bytes:
                    return await self.reject_request(scope, original_receive, send)
                chunks.append(body)
                if not message.get("more_body", False):
                    break
            buffered = b"".join(chunks)
            del chunks
            consumed = False

            async def replay_receive():
                nonlocal consumed, buffered
                if not consumed:
                    consumed = True
                    body, buffered = buffered, b""
                    return {"type": "http.request", "body": body, "more_body": False}
                return await original_receive()

            receive = replay_receive

        if not self.max_response_bytes:
            return await self.app(scope, receive, send)

        start, chunks, size, rejected = None, [], 0, False

        async def bounded_send(message):
            nonlocal start, size, rejected
            if rejected:
                return
            if message["type"] == "http.response.start":
                start = message
                return
            if message["type"] != "http.response.body":
                return await send(message)
            body = message.get("body", b"")
            size += len(body)
            if size > self.max_response_bytes:
                rejected = True
                chunks.clear()
                # The handler may already have saved its changes. Do not suggest
                # blindly repeating a write; the underlying data remains intact.
                response = JSONResponse({"detail": "This result is too large for this hosting plan. Your stored data has not been truncated. Use a smaller preview or export through a local installation; check saved changes before retrying a write."},
                                        status_code=413, headers={"Cache-Control": "no-store"})
                return await response(scope, receive, send)
            chunks.append(body)
            if not message.get("more_body", False):
                await send(start)
                await send({"type": "http.response.body", "body": b"".join(chunks), "more_body": False})
                chunks.clear()

        await self.app(scope, receive, bounded_send)

    async def reject_request(self, scope, receive, send):
        response = JSONResponse({"detail": "This request exceeds the hosting upload limit. Use a smaller file or fewer records. No changes were made."},
                                status_code=413, headers={"Cache-Control": "no-store"})
        await response(scope, receive, send)
