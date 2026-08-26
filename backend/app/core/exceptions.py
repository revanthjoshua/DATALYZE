from fastapi import HTTPException, status


class DatalyzeException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


class TenantIsolationException(DatalyzeException):
    def __init__(self, detail: str = "Access denied: Cross-tenant data access is strictly forbidden"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class AuthenticationException(DatalyzeException):
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class ResourceNotFoundException(DatalyzeException):
    def __init__(self, resource: str = "Resource"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=f"{resource} not found or does not belong to your company")


class DataValidationException(DatalyzeException):
    def __init__(self, detail: str = "Data validation failed"):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


class PermissionDeniedException(DatalyzeException):
    def __init__(self, detail: str = "You do not have permission to perform this action"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
