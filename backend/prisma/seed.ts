import { PrismaClient, Role } from "@prisma/client";
import bcrypt from "bcryptjs";

const prisma = new PrismaClient();

async function main() {
  const passwordHash = await bcrypt.hash("password123", 10);

  const garage = await prisma.garage.upsert({
    where: { email: "contact@garage-plateau.ci" },
    update: {},
    create: {
      name: "Garage du Plateau",
      city: "Abidjan",
      address: "Boulevard de la République, Plateau",
      phone: "+225 07 00 00 00 00",
      email: "contact@garage-plateau.ci",
      users: {
        create: {
          role: Role.GARAGE_ADMIN,
          name: "Admin Garage du Plateau",
          email: "admin@garage-plateau.ci",
          passwordHash,
        },
      },
    },
  });

  const client = await prisma.user.upsert({
    where: { email: "client@example.ci" },
    update: {},
    create: {
      role: Role.CLIENT,
      name: "Kouassi Yao",
      email: "client@example.ci",
      phone: "+225 05 00 00 00 00",
      passwordHash,
    },
  });

  console.log("Données de démo créées :", { garageId: garage.id, clientId: client.id });
  console.log("Mot de passe pour tous les comptes de démo : password123");
}

main()
  .catch((error) => {
    console.error(error);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
