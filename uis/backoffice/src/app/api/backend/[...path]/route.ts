import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const apiOrigin = (process.env.HEALTHCORE_API_ORIGIN || "http://127.0.0.1:8000").replace(/\/$/, "");
const localRfpProxySecret = process.env.RFP_LOCAL_PROXY_SECRET;

async function proxy(request: NextRequest, context: { params: { path?: string[] } }) {
  const path = (context.params.path ?? []).map(encodeURIComponent).join("/");
  if (!path) return NextResponse.json({ detail: "Backend path is required." }, { status: 400 });
  const upstreamUrl = new URL(`${apiOrigin}/${path}`);
  upstreamUrl.search = request.nextUrl.search;

  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  const authorization = request.headers.get("authorization");
  if (contentType) headers.set("content-type", contentType);
  if (authorization) headers.set("authorization", authorization);

  // Only the RFP API receives the server-side development credential. Tunnel
  // cookies, forwarded-host headers and other browser headers are not relayed.
  if (path === "rfp" || path.startsWith("rfp/")) {
    if (localRfpProxySecret) headers.set("x-healthcore-local-rfp-proxy", localRfpProxySecret);
  }

  const method = request.method.toUpperCase();
  const body = method === "GET" || method === "HEAD" ? undefined : await request.arrayBuffer();
  try {
    const upstream = await fetch(upstreamUrl, {
      method,
      headers,
      body,
      cache: "no-store",
      redirect: "manual",
    });
    const responseHeaders = new Headers();
    const responseContentType = upstream.headers.get("content-type");
    if (responseContentType) responseHeaders.set("content-type", responseContentType);
    const location = upstream.headers.get("location");
    if (location) responseHeaders.set("location", location);
    return new NextResponse(upstream.body, {
      status: upstream.status,
      headers: responseHeaders,
    });
  } catch {
    return NextResponse.json({ detail: "The HealthCore API is unavailable." }, { status: 502 });
  }
}

export const GET = proxy;
export const POST = proxy;
