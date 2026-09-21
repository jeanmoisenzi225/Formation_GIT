import { NextFunction, Request, Response } from "express";
import { Role } from "@prisma/client";
import { JwtPayload, verifyToken } from "../utils/jwt";

declare global {
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace Express {
    interface Request {
      auth?: JwtPayload;
    }
  }
}

export function requireAuth(req: Request, res: Response, next: NextFunction) {
  const header = req.headers.authorization;
  if (!header?.startsWith("Bearer ")) {
    return res.status(401).json({ error: "Authentification requise" });
  }

  const token = header.slice("Bearer ".length);
  try {
    req.auth = verifyToken(token);
    next();
  } catch {
    return res.status(401).json({ error: "Token invalide ou expiré" });
  }
}

export function requireRole(...roles: Role[]) {
  return (req: Request, res: Response, next: NextFunction) => {
    if (!req.auth || !roles.includes(req.auth.role)) {
      return res.status(403).json({ error: "Accès refusé" });
    }
    next();
  };
}
