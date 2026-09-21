export type Role = "CLIENT" | "GARAGE_ADMIN" | "GARAGE_STAFF";

export type AppointmentStatus = "PENDING" | "CONFIRMED" | "REFUSED" | "CANCELLED" | "COMPLETED";

export type WorkOrderStatus = "NOT_STARTED" | "IN_PROGRESS" | "WAITING_PARTS" | "COMPLETED";

export interface AuthUser {
  id: string;
  role: Role;
  name: string;
  email: string;
  garageId: string | null;
}

export interface Garage {
  id: string;
  name: string;
  city: string;
  address: string;
  phone: string;
  email: string | null;
}

export interface Vehicle {
  id: string;
  brand: string;
  model: string;
  plateNumber: string;
  year: number | null;
  createdAt: string;
}

export interface WorkOrderUpdate {
  id: string;
  status: WorkOrderStatus;
  comment: string | null;
  createdAt: string;
}

export interface WorkOrder {
  id: string;
  status: WorkOrderStatus;
  notes: string | null;
  costEstimate: number | null;
  startedAt: string | null;
  completedAt: string | null;
  updates: WorkOrderUpdate[];
}

export interface Appointment {
  id: string;
  requestedDate: string;
  serviceType: string;
  description: string | null;
  status: AppointmentStatus;
  garage: { id: string; name: string; city: string; phone: string };
  client: { id: string; name: string; phone: string | null; email: string };
  vehicle: Vehicle;
  workOrder: WorkOrder | null;
}
