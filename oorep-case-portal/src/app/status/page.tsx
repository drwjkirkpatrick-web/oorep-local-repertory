import { Suspense } from "react";
import StatusPage from "./StatusPage";

export default function StatusPageWrapper() {
  return (
    <Suspense fallback={<div className="max-w-2xl mx-auto px-6 py-12"><p>Loading...</p></div>}>
      <StatusPage />
    </Suspense>
  );
}
