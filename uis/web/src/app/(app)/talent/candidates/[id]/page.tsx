import { CandidateDetailPage } from "@/features/talent/components/CandidateDetailPage";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function CandidatePage({ params }: PageProps) {
  const { id } = await params;
  return <CandidateDetailPage id={id} />;
}
