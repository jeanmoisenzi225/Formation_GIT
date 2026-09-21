import { Router } from "express";
import { AppointmentStatus, Role, WorkOrderStatus } from "@prisma/client";
import { prisma } from "../../db/prisma";
import { asyncHandler, HttpError } from "../../middleware/errorHandler";
import { requireAuth, requireRole } from "../../middleware/auth";
import { createAppointmentSchema, updateAppointmentStatusSchema } from "./appointments.schemas";

export const appointmentsRouter = Router();

appointmentsRouter.use(requireAuth);

const appointmentInclude = {
  garage: { select: { id: true, name: true, city: true, phone: true } },
  client: { select: { id: true, name: true, phone: true, email: true } },
  vehicle: true,
  workOrder: { include: { updates: { orderBy: { createdAt: "asc" as const } } } },
};

// Le client crée une demande de rendez-vous
appointmentsRouter.post(
  "/",
  requireRole(Role.CLIENT),
  asyncHandler(async (req, res) => {
    const input = createAppointmentSchema.parse(req.body);

    const vehicle = await prisma.vehicle.findUnique({ where: { id: input.vehicleId } });
    if (!vehicle || vehicle.clientId !== req.auth!.userId) {
      throw new HttpError(404, "Véhicule introuvable");
    }

    const garage = await prisma.garage.findUnique({ where: { id: input.garageId } });
    if (!garage) {
      throw new HttpError(404, "Garage introuvable");
    }

    const appointment = await prisma.appointment.create({
      data: {
        garageId: input.garageId,
        vehicleId: input.vehicleId,
        clientId: req.auth!.userId,
        requestedDate: input.requestedDate,
        serviceType: input.serviceType,
        description: input.description,
      },
      include: appointmentInclude,
    });

    res.status(201).json(appointment);
  })
);

// Le client consulte ses propres rendez-vous
appointmentsRouter.get(
  "/mine",
  requireRole(Role.CLIENT),
  asyncHandler(async (req, res) => {
    const appointments = await prisma.appointment.findMany({
      where: { clientId: req.auth!.userId },
      include: appointmentInclude,
      orderBy: { requestedDate: "desc" },
    });
    res.json(appointments);
  })
);

// Le garage consulte les rendez-vous qui lui sont adressés
appointmentsRouter.get(
  "/garage",
  requireRole(Role.GARAGE_ADMIN, Role.GARAGE_STAFF),
  asyncHandler(async (req, res) => {
    const status = req.query.status;
    const appointments = await prisma.appointment.findMany({
      where: {
        garageId: req.auth!.garageId!,
        status: typeof status === "string" ? (status as AppointmentStatus) : undefined,
      },
      include: appointmentInclude,
      orderBy: { requestedDate: "asc" },
    });
    res.json(appointments);
  })
);

// Mise à jour du statut : le garage confirme/refuse/termine, le client peut annuler
appointmentsRouter.patch(
  "/:id/status",
  asyncHandler(async (req, res) => {
    const { status } = updateAppointmentStatusSchema.parse(req.body);
    const appointment = await prisma.appointment.findUnique({ where: { id: req.params.id } });
    if (!appointment) {
      throw new HttpError(404, "Rendez-vous introuvable");
    }

    const isGarageStaff =
      (req.auth!.role === Role.GARAGE_ADMIN || req.auth!.role === Role.GARAGE_STAFF) &&
      req.auth!.garageId === appointment.garageId;
    const isOwningClient = req.auth!.role === Role.CLIENT && req.auth!.userId === appointment.clientId;

    if (!isGarageStaff && !isOwningClient) {
      throw new HttpError(403, "Accès refusé");
    }

    if (isOwningClient && status !== "CANCELLED") {
      throw new HttpError(403, "Le client ne peut qu'annuler un rendez-vous");
    }

    if (["REFUSED", "CANCELLED", "COMPLETED"].includes(appointment.status)) {
      throw new HttpError(400, "Ce rendez-vous est déjà clôturé");
    }

    await prisma.appointment.update({
      where: { id: req.params.id },
      data: { status: status as AppointmentStatus },
    });

    // À la confirmation, on ouvre automatiquement le suivi des travaux
    if (status === "CONFIRMED") {
      await prisma.workOrder.upsert({
        where: { appointmentId: appointment.id },
        update: {},
        create: {
          appointmentId: appointment.id,
          status: WorkOrderStatus.NOT_STARTED,
          updates: {
            create: { status: WorkOrderStatus.NOT_STARTED, comment: "Rendez-vous confirmé" },
          },
        },
      });
    }

    const updated = await prisma.appointment.findUniqueOrThrow({
      where: { id: req.params.id },
      include: appointmentInclude,
    });

    res.json(updated);
  })
);
