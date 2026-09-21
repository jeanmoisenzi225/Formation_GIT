import { Role } from "@prisma/client";
import { prisma } from "../../db/prisma";
import { HttpError } from "../../middleware/errorHandler";
import { signToken } from "../../utils/jwt";
import { hashPassword, verifyPassword } from "../../utils/password";
import {
  registerClientSchema,
  registerGarageSchema,
  registerStaffSchema,
  loginSchema,
} from "./auth.schemas";
import { z } from "zod";

function toAuthResponse(user: {
  id: string;
  role: Role;
  name: string;
  email: string;
  garageId: string | null;
}) {
  const token = signToken({ userId: user.id, role: user.role, garageId: user.garageId });
  return {
    token,
    user: {
      id: user.id,
      role: user.role,
      name: user.name,
      email: user.email,
      garageId: user.garageId,
    },
  };
}

export async function registerClient(input: z.infer<typeof registerClientSchema>) {
  const existing = await prisma.user.findUnique({ where: { email: input.email } });
  if (existing) {
    throw new HttpError(409, "Un compte existe déjà avec cet email");
  }

  const passwordHash = await hashPassword(input.password);
  const user = await prisma.user.create({
    data: {
      role: Role.CLIENT,
      name: input.name,
      email: input.email,
      phone: input.phone,
      passwordHash,
    },
  });

  return toAuthResponse(user);
}

export async function registerGarage(input: z.infer<typeof registerGarageSchema>) {
  // Cette application ne gère qu'un seul garage : cette route ne sert qu'au
  // tout premier démarrage (bootstrap) et se ferme ensuite d'elle-même.
  const alreadyConfigured = await prisma.garage.findFirst();
  if (alreadyConfigured) {
    throw new HttpError(409, "Le garage est déjà configuré");
  }

  const existingUser = await prisma.user.findUnique({ where: { email: input.adminEmail } });
  if (existingUser) {
    throw new HttpError(409, "Un compte existe déjà avec cet email");
  }

  const passwordHash = await hashPassword(input.adminPassword);

  const garage = await prisma.garage.create({
    data: {
      name: input.garageName,
      city: input.city,
      address: input.address,
      phone: input.garagePhone,
      email: input.garageEmail,
      users: {
        create: {
          role: Role.GARAGE_ADMIN,
          name: input.adminName,
          email: input.adminEmail,
          passwordHash,
        },
      },
    },
    include: { users: true },
  });

  const admin = garage.users[0];
  return toAuthResponse(admin);
}

export async function registerStaff(garageId: string, input: z.infer<typeof registerStaffSchema>) {
  const existing = await prisma.user.findUnique({ where: { email: input.email } });
  if (existing) {
    throw new HttpError(409, "Un compte existe déjà avec cet email");
  }

  const passwordHash = await hashPassword(input.password);
  const user = await prisma.user.create({
    data: {
      role: Role.GARAGE_STAFF,
      name: input.name,
      email: input.email,
      passwordHash,
      garageId,
    },
  });

  return toAuthResponse(user);
}

export async function login(input: z.infer<typeof loginSchema>) {
  const user = await prisma.user.findUnique({ where: { email: input.email } });
  if (!user) {
    throw new HttpError(401, "Email ou mot de passe incorrect");
  }

  const valid = await verifyPassword(input.password, user.passwordHash);
  if (!valid) {
    throw new HttpError(401, "Email ou mot de passe incorrect");
  }

  return toAuthResponse(user);
}
