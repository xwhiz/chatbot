import { jwtVerify } from "jose";

export const decodeToken = async (token: string | undefined) => {
  if (!token) {
    return null;
  }
  try {
    const key = process.env.NEXT_PUBLIC_JWT_SECRET;
    const secret = new TextEncoder().encode(key);
    const decoded = await jwtVerify(token, secret);
    return decoded.payload;
  } catch (error) {
    console.error(error);
    return null;
  }
};
