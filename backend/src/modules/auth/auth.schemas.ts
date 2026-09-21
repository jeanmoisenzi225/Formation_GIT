import { z } from "zod";

export const registerClientSchema = z.object({
  name: z.string().min(2),
  email: z.string().email(),
  phone: z.string().min(8).optional(),
  password: z.string().min(6),
});

export const registerGarageSchema = z.object({
  garageName: z.string().min(2),
  city: z.string().min(2),
  address: z.string().min(2),
  garagePhone: z.string().min(8),
  garageEmail: z.string().email().optional(),
  adminName: z.string().min(2),
  adminEmail: z.string().email(),
  adminPassword: z.string().min(6),
});

export const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
});
