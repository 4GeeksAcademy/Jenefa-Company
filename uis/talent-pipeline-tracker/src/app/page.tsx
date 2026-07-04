import { Suspense } from "react";
import { CandidateListPage } from "@/components/CandidateListPage";

export default function HomePage() {
  return (
    <Suspense
      fallback={
        <div className="rounded-lg border border-teal-200 bg-teal-50 px-6 py-8 text-center text-teal-800">
          Loading candidate roster…
        </div>
      }
    >
      <CandidateListPage />
    </Suspense>
  );
}
