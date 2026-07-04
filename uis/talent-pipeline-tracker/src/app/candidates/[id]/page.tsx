import { CandidateDetailPage } from "@/components/CandidateDetailPage";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function CandidatePage({ params }: PageProps) {
  const { id } = await params;
  return <CandidateDetailPage id={id} />;
}
