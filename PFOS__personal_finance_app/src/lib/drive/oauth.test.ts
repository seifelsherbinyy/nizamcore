/**
 * Google GIS scope isolation regression.
 * Owning authority: KIRO Contract 2 / Phase 2.1; drive-db.md exact drive.file invariant.
 *
 * All values are synthetic. No OAuth credential or token appears here. The regression reproduces the
 * owner-observed failure where GIS merged a prior Drive grant into the requested token and NIZAM
 * correctly refused the broader result.
 */
import { afterEach, describe, expect, it, vi } from 'vitest';
import { DRIVE_FILE_SCOPE, __setSessionForTests, signIn } from './oauth.ts';

afterEach(() => {
  __setSessionForTests(null);
  delete window.google;
});

describe('GIS token request stays isolated to drive.file', () => {
  it('disables incremental granted-scope merging in the token-client configuration', async () => {
    let config: Record<string, unknown> | null = null;
    const requestAccessToken = vi.fn(() => {
      const callback = config?.callback as ((response: Record<string, unknown>) => void) | undefined;
      callback?.({
        access_token: 'synthetic-access-token',
        expires_in: 60,
        scope: DRIVE_FILE_SCOPE,
      });
    });
    window.google = {
      accounts: {
        oauth2: {
          initTokenClient: vi.fn((received: Record<string, unknown>) => {
            config = received;
            return { requestAccessToken };
          }),
          revoke: vi.fn(),
        },
      },
    } as unknown as typeof window.google;

    await expect(signIn()).resolves.toMatchObject({ grantedScope: DRIVE_FILE_SCOPE });
    expect(config).toMatchObject({
      scope: DRIVE_FILE_SCOPE,
      include_granted_scopes: false,
    });
    expect(requestAccessToken).toHaveBeenCalledWith({ prompt: '' });
  });
});
