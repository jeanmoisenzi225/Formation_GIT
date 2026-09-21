import { AppointmentStatus, WorkOrderStatus } from "../api/types";

const APPOINTMENT_LABELS: Record<AppointmentStatus, string> = {
  PENDING: "En attente",
  CONFIRMED: "Confirmé",
  REFUSED: "Refusé",
  CANCELLED: "Annulé",
  COMPLETED: "Terminé",
};

const WORK_ORDER_LABELS: Record<WorkOrderStatus, string> = {
  NOT_STARTED: "Pas commencé",
  IN_PROGRESS: "En cours",
  WAITING_PARTS: "En attente de pièces",
  COMPLETED: "Terminé",
};

export function AppointmentStatusBadge({ status }: { status: AppointmentStatus }) {
  return <span className={`badge badge-${status.toLowerCase()}`}>{APPOINTMENT_LABELS[status]}</span>;
}

export function WorkOrderStatusBadge({ status }: { status: WorkOrderStatus }) {
  return <span className={`badge badge-${status.toLowerCase()}`}>{WORK_ORDER_LABELS[status]}</span>;
}
