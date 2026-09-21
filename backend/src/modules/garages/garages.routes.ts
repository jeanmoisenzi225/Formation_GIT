import { Router } from "express";
import { Role } from "@prisma/client";
import { prisma } from "../../db/prisma";
import { asyncHandler, HttpError } from "../../middleware/errorHandler";
import { requireAuth, requireRole } from "../../middleware/auth";
import { updateGarageSchema } from "./garages.schemas";

export const garagesRouter = Router();

// L'application ne gère qu'un seul garage : ses informations publiques
garagesRouter.get(
  "/",
  asyncHandler(async (_req, res) => {
    const garage = await prisma.garage.findFirst({
      select: {
        id: true,
        name: true,
        city: true,
        address: true,
        phone: true,
        email: true,
      },
    });
    if (!garage) {
      throw new HttpError(404, "Le garage n'est pas encore configuré");
    }
    res.json(garage);
  })
);

garagesRouter.patch(
  "/",
  requireAuth,
  requireRole(Role.GARAGE_ADMIN),
  asyncHandler(async (req, res) => {
    const input = updateGarageSchema.parse(req.body);
    const garage = await prisma.garage.update({
      where: { id: req.auth!.garageId! },
      data: input,
    });
    res.json(garage);
  })
);
