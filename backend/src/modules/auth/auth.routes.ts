import { Router } from "express";
import { Role } from "@prisma/client";
import { asyncHandler } from "../../middleware/errorHandler";
import { requireAuth, requireRole } from "../../middleware/auth";
import {
  registerClientSchema,
  registerGarageSchema,
  registerStaffSchema,
  loginSchema,
} from "./auth.schemas";
import { login, registerClient, registerGarage, registerStaff } from "./auth.service";

export const authRouter = Router();

authRouter.post(
  "/register/client",
  asyncHandler(async (req, res) => {
    const input = registerClientSchema.parse(req.body);
    const result = await registerClient(input);
    res.status(201).json(result);
  })
);

authRouter.post(
  "/register/garage",
  asyncHandler(async (req, res) => {
    const input = registerGarageSchema.parse(req.body);
    const result = await registerGarage(input);
    res.status(201).json(result);
  })
);

authRouter.post(
  "/register/staff",
  requireAuth,
  requireRole(Role.GARAGE_ADMIN),
  asyncHandler(async (req, res) => {
    const input = registerStaffSchema.parse(req.body);
    const result = await registerStaff(req.auth!.garageId!, input);
    res.status(201).json(result);
  })
);

authRouter.post(
  "/login",
  asyncHandler(async (req, res) => {
    const input = loginSchema.parse(req.body);
    const result = await login(input);
    res.status(200).json(result);
  })
);
