import { EditCandidatePage } from "@/features/talent/components/EditCandidatePage";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function EditCandidateRoute({ params }: PageProps) {
  const { id } = await params;
  return <EditCandidatePage id={id} />;
}
