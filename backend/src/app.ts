import express from "express";
import cors from "cors";
import { env } from "./config/env";
import { errorHandler } from "./middleware/errorHandler";
import { authRouter } from "./modules/auth/auth.routes";
import { garagesRouter } from "./modules/garages/garages.routes";
import { vehiclesRouter } from "./modules/vehicles/vehicles.routes";
import { appointmentsRouter } from "./modules/appointments/appointments.routes";
import { workOrdersRouter } from "./modules/workOrders/workOrders.routes";

export function createApp() {
  const app = express();

  app.use(cors({ origin: env.corsOrigin, credentials: true }));
  app.use(express.json());

  app.get("/health", (_req, res) => res.json({ status: "ok" }));

  app.use("/api/auth", authRouter);
  app.use("/api/garages", garagesRouter);
  app.use("/api/vehicles", vehiclesRouter);
  app.use("/api/appointments", appointmentsRouter);
  app.use("/api/work-orders", workOrdersRouter);

  app.use(errorHandler);

  return app;
}
