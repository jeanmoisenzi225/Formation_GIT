import { Router } from "express";
import { Role } from "@prisma/client";
import { prisma } from "../../db/prisma";
import { asyncHandler, HttpError } from "../../middleware/errorHandler";
import { requireAuth, requireRole } from "../../middleware/auth";
import { updateGarageSchema } from "./garages.schemas";

export const garagesRouter = Router();

// Liste publique des garages (recherche par ville en option)
garagesRouter.get(
  "/",
  asyncHandler(async (req, res) => {
    const city = typeof req.query.city === "string" ? req.query.city : undefined;
    const garages = await prisma.garage.findMany({
      where: city ? { city: { equals: city, mode: "insensitive" } } : undefined,
      select: {
        id: true,
        name: true,
        city: true,
        address: true,
        phone: true,
        email: true,
      },
      orderBy: { name: "asc" },
    });
    res.json(garages);
  })
);

garagesRouter.get(
  "/:id",
  asyncHandler(async (req, res) => {
    const garage = await prisma.garage.findUnique({
      where: { id: req.params.id },
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
      throw new HttpError(404, "Garage introuvable");
    }
    res.json(garage);
  })
);

garagesRouter.patch(
  "/:id",
  requireAuth,
  requireRole(Role.GARAGE_ADMIN),
  asyncHandler(async (req, res) => {
    if (req.auth!.garageId !== req.params.id) {
      throw new HttpError(403, "Vous ne pouvez modifier que votre propre garage");
    }
    const input = updateGarageSchema.parse(req.body);
    const garage = await prisma.garage.update({
      where: { id: req.params.id },
      data: input,
    });
    res.json(garage);
  })
);
