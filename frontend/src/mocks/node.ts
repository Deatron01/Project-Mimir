import { setupServer } from 'msw/node';
import { makeHandlers } from './handlers';

export const TEST_API_BASE = 'http://localhost/api/v1';
export const server = setupServer(...makeHandlers(TEST_API_BASE));
