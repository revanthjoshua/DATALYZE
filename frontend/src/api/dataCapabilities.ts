import axiosClient from './axiosClient';
import { assertFileWithinLimit, assertJsonWithinLimit, type DataCapabilities } from '../utils/payloadLimits';

export async function getDataCapabilities(): Promise<DataCapabilities> {
  return (await axiosClient.get<DataCapabilities>('/data/capabilities')).data;
}

export async function checkUploadSize(file: File): Promise<void> {
  assertFileWithinLimit(file, await getDataCapabilities());
}

export async function checkRequestSize(payload: unknown): Promise<void> {
  assertJsonWithinLimit(payload, await getDataCapabilities());
}
