import { z } from "zod";

export const updateWorkOrderSchema = z.object({
  status: z.enum(["NOT_STARTED", "IN_PROGRESS", "WAITING_PARTS", "COMPLETED"]),
  comment: z.string().optional(),
  costEstimate: z.number().nonnegative().optional(),
});
