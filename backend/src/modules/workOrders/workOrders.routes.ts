import { Router } from "express";
import { Role, WorkOrderStatus } from "@prisma/client";
import { prisma } from "../../db/prisma";
import { asyncHandler, HttpError } from "../../middleware/errorHandler";
import { requireAuth, requireRole } from "../../middleware/auth";
import { updateWorkOrderSchema } from "./workOrders.schemas";

export const workOrdersRouter = Router();

workOrdersRouter.use(requireAuth);

async function getWorkOrderWithAppointment(id: string) {
  const workOrder = await prisma.workOrder.findUnique({
    where: { id },
    include: {
      appointment: true,
      updates: { orderBy: { createdAt: "asc" } },
    },
  });
  if (!workOrder) {
    throw new HttpError(404, "Suivi de travaux introuvable");
  }
  return workOrder;
}

// Consultation par le client propriétaire ou le garage concerné
workOrdersRouter.get(
  "/:id",
  asyncHandler(async (req, res) => {
    const workOrder = await getWorkOrderWithAppointment(req.params.id);

    const isGarageStaff =
      (req.auth!.role === Role.GARAGE_ADMIN || req.auth!.role === Role.GARAGE_STAFF) &&
      req.auth!.garageId === workOrder.appointment.garageId;
    const isOwningClient =
      req.auth!.role === Role.CLIENT && req.auth!.userId === workOrder.appointment.clientId;

    if (!isGarageStaff && !isOwningClient) {
      throw new HttpError(403, "Accès refusé");
    }

    res.json(workOrder);
  })
);

// Mise à jour du statut par le garage : suivi quasi temps réel pour le client
workOrdersRouter.patch(
  "/:id",
  requireRole(Role.GARAGE_ADMIN, Role.GARAGE_STAFF),
  asyncHandler(async (req, res) => {
    const workOrder = await getWorkOrderWithAppointment(req.params.id);
    if (workOrder.appointment.garageId !== req.auth!.garageId) {
      throw new HttpError(403, "Accès refusé");
    }

    const input = updateWorkOrderSchema.parse(req.body);
    const newStatus = input.status as WorkOrderStatus;

    const updated = await prisma.workOrder.update({
      where: { id: req.params.id },
      data: {
        status: newStatus,
        costEstimate: input.costEstimate,
        startedAt: newStatus === "IN_PROGRESS" && !workOrder.startedAt ? new Date() : undefined,
        completedAt: newStatus === "COMPLETED" ? new Date() : undefined,
        updates: {
          create: { status: newStatus, comment: input.comment },
        },
      },
      include: { updates: { orderBy: { createdAt: "asc" } } },
    });

    if (newStatus === "COMPLETED") {
      await prisma.appointment.update({
        where: { id: workOrder.appointmentId },
        data: { status: "COMPLETED" },
      });
    }

    res.json(updated);
  })
);
