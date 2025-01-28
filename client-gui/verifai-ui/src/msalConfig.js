import { Configuration } from "@azure/msal-browser";

const clientId = process.env.REACT_APP_AZURE_CLIENT_ID;
const tenantId = process.env.REACT_APP_AZURE_TENANT_ID;
const redirectURL = process.env.REACT_APP_AZURE_REDIRECT_URL ;

export const isSSOConfigured = !!(clientId && tenantId);

export const msalConfig = isSSOConfigured ? {
  auth: {
    clientId: clientId,
    authority: tenantId,
    knownAuthorities: ["login.microsoftonline.com","sts.windows.net"],
    redirectUri: redirectURL
  },
  cache: {
    cacheLocation: "sessionStorage",
    storeAuthStateInCookie: false,
  },
} : null;

export const loginRequest = {
  scopes: ["openid"]
};