# OIDC Setup

Scanopy supports single sign-on (SSO) with any OpenID Connect (OIDC) compliant identity provider, such as Google Workspace, Microsoft Entra ID, or Okta.

> **Caution**
> OIDC setup is only available for self-hosted deployments.

## Configuration

OIDC is configured via environment variables. See [Environment Files](/docs/self-hosted/server-configuration/#environment-files) for how to manage these.

### Required Parameters

*   `SCANOPY_OIDC_CLIENT_ID`: Your OIDC client ID.
*   `SCANOPY_OIDC_CLIENT_SECRET`: Your OIDC client secret.
*   `SCANOPY_OIDC_ISSUER_URL`: The URL of your OIDC provider (e.g., `https://accounts.google.com`).

### Optional Parameters

*   `SCANOPY_OIDC_BUTTON_TEXT`: Text to display on the OIDC login button.
    *   Default: “Sign in with OIDC”
*   `SCANOPY_OIDC_SCOPES`: OIDC scopes to request.
    *   Default: `openid profile email`
*   `SCANOPY_OIDC_ADMIN_ROLES`: A comma-separated list of role names from your identity provider that should be granted Admin access in Scanopy.
*   `SCANOPY_OIDC_USER_ROLES`: A comma-separated list of role names from your identity provider that should be granted User access in Scanopy.

## Redirect URI

When configuring your OIDC provider, you will need to provide a redirect URI. The path for this is `/oidc/callback`.

Example: `https://your-scanopy-url.com/oidc/callback`

## Role Mapping

You can map roles from your identity provider to Scanopy roles using the `SCANOPY_OIDC_ADMIN_ROLES` and `SCANOPY_OIDC_USER_ROLES` environment variables. This allows you to manage user access centrally in your identity provider.

If a user has a role that is in both lists, the Admin role will take precedence.

If a user does not have a role that is in either list, they will be granted the default role of User.

## Example Configurations

### Google Workspace

```
SCANOPY_OIDC_CLIENT_ID="your-google-client-id"
SCANOPY_OIDC_CLIENT_SECRET="your-google-client-secret"
SCANOPY_OIDC_ISSUER_URL="https://accounts.google.com"
SCANOPY_OIDC_BUTTON_TEXT="Sign in with Google"
```

### Microsoft Entra ID (Azure AD)

```
SCANOPY_OIDC_CLIENT_ID="your-entra-id-client-id"
SCANOPY_OIDC_CLIENT_SECRET="your-entra-id-client-secret"
SCANOPY_OIDC_ISSUER_URL="https://login.microsoftonline.com/your-tenant-id/v2.0"
SCANOPY_OIDC_BUTTON_TEXT="Sign in with Microsoft"
```

### Okta

```
SCANOPY_OIDC_CLIENT_ID="your-okta-client-id"
SCANOPY_OIDC_CLIENT_SECRET="your-okta-client-secret"
SCANOPY_OIDC_ISSUER_URL="https://your-okta-domain.okta.com"
SCANOPY_OIDC_BUTTON_TEXT="Sign in with Okta"
```
