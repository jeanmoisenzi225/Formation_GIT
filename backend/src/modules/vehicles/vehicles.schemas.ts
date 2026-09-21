import { z } from "zod";

export const createVehicleSchema = z.object({
  brand: z.string().min(1),
  model: z.string().min(1),
  plateNumber: z.string().min(2),
  year: z.number().int().min(1950).max(2100).optional(),
});

export const updateVehicleSchema = createVehicleSchema.partial();
