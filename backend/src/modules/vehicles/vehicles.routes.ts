import { Router } from "express";
import { Role } from "@prisma/client";
import { prisma } from "../../db/prisma";
import { asyncHandler, HttpError } from "../../middleware/errorHandler";
import { requireAuth, requireRole } from "../../middleware/auth";
import { createVehicleSchema, updateVehicleSchema } from "./vehicles.schemas";

export const vehiclesRouter = Router();

vehiclesRouter.use(requireAuth, requireRole(Role.CLIENT));

vehiclesRouter.get(
  "/",
  asyncHandler(async (req, res) => {
    const vehicles = await prisma.vehicle.findMany({
      where: { clientId: req.auth!.userId },
      orderBy: { createdAt: "desc" },
    });
    res.json(vehicles);
  })
);

vehiclesRouter.post(
  "/",
  asyncHandler(async (req, res) => {
    const input = createVehicleSchema.parse(req.body);
    const vehicle = await prisma.vehicle.create({
      data: { ...input, clientId: req.auth!.userId },
    });
    res.status(201).json(vehicle);
  })
);

async function getOwnedVehicle(id: string, clientId: string) {
  const vehicle = await prisma.vehicle.findUnique({ where: { id } });
  if (!vehicle || vehicle.clientId !== clientId) {
    throw new HttpError(404, "Véhicule introuvable");
  }
  return vehicle;
}

vehiclesRouter.patch(
  "/:id",
  asyncHandler(async (req, res) => {
    await getOwnedVehicle(req.params.id, req.auth!.userId);
    const input = updateVehicleSchema.parse(req.body);
    const vehicle = await prisma.vehicle.update({
      where: { id: req.params.id },
      data: input,
    });
    res.json(vehicle);
  })
);

vehiclesRouter.delete(
  "/:id",
  asyncHandler(async (req, res) => {
    await getOwnedVehicle(req.params.id, req.auth!.userId);
    await prisma.vehicle.delete({ where: { id: req.params.id } });
    res.status(204).send();
  })
);

// Historique du véhicule : tous les rendez-vous et l'état de leurs travaux
vehiclesRouter.get(
  "/:id/history",
  asyncHandler(async (req, res) => {
    await getOwnedVehicle(req.params.id, req.auth!.userId);
    const appointments = await prisma.appointment.findMany({
      where: { vehicleId: req.params.id },
      include: {
        garage: { select: { id: true, name: true, city: true } },
        workOrder: { include: { updates: { orderBy: { createdAt: "asc" } } } },
      },
      orderBy: { requestedDate: "desc" },
    });
    res.json(appointments);
  })
);
