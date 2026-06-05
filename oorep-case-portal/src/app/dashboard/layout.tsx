import Link from "next/link";
import { redirect } from "next/navigation";
import { ReactNode } from "react";
import { requireAdminSession } from "@/lib/adminAuth";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const auth = requireAdminSession();
  if (!auth.ok) {
    redirect("/admin/login");
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top bar */}
      <header className="bg-gray-900 text-white px-6 py-3 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center gap-4">
          <Link href="/dashboard" className="font-bold text-lg">
            OORep Clinical Dashboard
          </Link>
          <span className="text-gray-400">/</span>
          <span className="text-sm text-gray-300">Practitioner Only</span>
        </div>
        <nav className="flex gap-4 text-sm">
          <Link href="/dashboard" className="hover:text-blue-300 transition">
            Dashboard
          </Link>
          <Link href="/dashboard/pipeline" className="hover:text-blue-300 transition">
            Pipeline Builder
          </Link>
          <Link href="/admin" className="hover:text-blue-300 transition">
            Admin
          </Link>
        </nav>
      </header>
      {children}
    </div>
  );
}
