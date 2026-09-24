import { describe, expect, it } from 'vitest';
import { validateFiles } from './Dropzone';
import { DEFAULT_LIMITS } from '../../api/types';

const f = (name: string, size = 10) => new File([new Uint8Array(size)], name);

describe('validateFiles', () => {
  it('accepts allowed types', () => {
    const { accepted, rejected } = validateFiles([f('a.pdf'), f('b.TXT'), f('c.docx'), f('d.md')], []);
    expect(accepted).toHaveLength(4);
    expect(rejected).toHaveLength(0);
  });
  it('rejects wrong type, oversize and duplicates', () => {
    const big = f('big.pdf', DEFAULT_LIMITS.max_file_bytes + 1);
    const { rejected } = validateFiles([f('x.exe'), big, f('a.pdf')], [f('a.pdf')]);
    expect(rejected.map((r) => r.reason)).toEqual(['type', 'size', 'duplicate']);
  });
  it('enforces per-upload and per-topic counts', () => {
    const many = Array.from({ length: 12 }, (_, i) => f(`f${i}.txt`));
    expect(validateFiles(many, []).accepted).toHaveLength(DEFAULT_LIMITS.max_files_per_upload);
    expect(validateFiles([f('z.txt')], [], { existingCount: DEFAULT_LIMITS.max_files_per_topic }).rejected[0].reason).toBe('count');
  });
  it('enforces topic storage', () => {
    const r = validateFiles([f('z.txt', 100)], [], { existingBytes: DEFAULT_LIMITS.max_topic_bytes - 50 });
    expect(r.rejected[0].reason).toBe('storage');
  });
});
