import { z } from "zod";

export const createAppointmentSchema = z.object({
  garageId: z.string().uuid(),
  vehicleId: z.string().uuid(),
  requestedDate: z.coerce.date(),
  serviceType: z.string().min(2),
  description: z.string().optional(),
});

export const updateAppointmentStatusSchema = z.object({
  status: z.enum(["CONFIRMED", "REFUSED", "CANCELLED", "COMPLETED"]),
});
