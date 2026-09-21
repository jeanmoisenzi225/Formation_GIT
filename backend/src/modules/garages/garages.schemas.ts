import { z } from "zod";

export const updateGarageSchema = z.object({
  name: z.string().min(2).optional(),
  city: z.string().min(2).optional(),
  address: z.string().min(2).optional(),
  phone: z.string().min(8).optional(),
  email: z.string().email().optional(),
});
