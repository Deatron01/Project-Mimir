import { motion } from 'framer-motion';

/** Shared frame for the auth pages. */
export default function AuthCard({ title, subtitle, children, footer }: { title: string; subtitle?: string; children: React.ReactNode; footer?: React.ReactNode }) {
  return (
    <div className="relative flex min-h-[80vh] items-center justify-center overflow-hidden py-10">
      <div className="pointer-events-none absolute left-[-10%] top-[20%] h-[40rem] w-[40rem] rounded-full bg-primary/20 blur-[120px]" aria-hidden="true" />
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="z-10 w-full max-w-md px-6">
        <div className="card relative overflow-hidden p-8">
          <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-accent to-primary" />
          <div className="mb-8 text-center">
            <h1 className="mb-2 text-3xl font-extrabold tracking-tight">{title}</h1>
            {subtitle && <p className="text-sm text-muted">{subtitle}</p>}
          </div>
          {children}
          {footer && <div className="mt-6 text-center text-sm text-muted">{footer}</div>}
        </div>
      </motion.div>
    </div>
  );
}
