import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen">
      {/* Hero Section */}
      <section className="bg-gray-900 text-white py-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl md:text-5xl font-bold mb-4">OORep Case Portal</h1>
          <p className="text-lg text-gray-300 mb-6">
            Professional homeopathic repertory case analysis by a licensed naturopathic physician
          </p>
          <p className="text-sm text-gray-400 mb-8">
            ⚕️ This service is for non-diagnostic, informational purposes only and does not constitute medical advice.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/submit" className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition">
              Submit a Case — $49
            </Link>
            <Link href="/status" className="px-6 py-3 bg-gray-700 text-white rounded-lg font-medium hover:bg-gray-600 transition">
              Check Status
            </Link>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-16 px-6 max-w-4xl mx-auto">
        <h2 className="text-2xl font-bold mb-8 text-center">How It Works</h2>
        <div className="grid md:grid-cols-3 gap-6">
          {[
            { step: "1", title: "Submit Anonymized Case", desc: "Fill the case form with chief concern, modalities, and detailed case notes. Remove any identifying information." },
            { step: "2", title: "Pay & Upload", desc: "Secure $49 payment via Stripe. Upload supporting documents (TXT, PDF, DOC, audio)." },
            { step: "3", title: "Receive Repertory Report", desc: "Admin reviews, runs OOREP repertorization, generates a final PDF analysis. Track via your case code." },
          ].map((s) => (
            <div key={s.step} className="border rounded-lg p-5 hover:shadow-md transition">
              <div className="text-xs font-mono text-gray-400 mb-2">Step {s.step}</div>
              <h3 className="font-semibold mb-2">{s.title}</h3>
              <p className="text-sm text-gray-600">{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Privacy & Safety */}
      <section className="bg-gray-50 py-12 px-6">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-xl font-bold mb-4">Privacy & Documentation</h2>
          <ul className="space-y-2 text-sm text-gray-700">
            <li>• Cases are <strong>anonymized</strong> — never include patient names, birthdates, or identifying details.</li>
            <li>• Uploads accepted: text, Word, PDF, Markdown, audio files.</li>
            <li>• All reports include a disclaimer that this is for educational/research purposes and does not replace professional medical evaluation.</li>
          </ul>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-8 px-6 text-center text-xs text-gray-500">
        OORep Case Portal • Built for naturopathic practitioners • Admin: <Link href="/admin/login" className="underline">Login</Link>
      </footer>
    </main>
  );
}
