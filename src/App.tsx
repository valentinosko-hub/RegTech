import { Navigate, Route, Routes } from 'react-router-dom';

import { CaseDetail } from '@/components/cases/CaseDetail';
import { Layout } from '@/components/layout/Layout';
import { Cases } from '@/routes/Cases';
import { Home } from '@/routes/Home';
import { Monitoring } from '@/routes/Monitoring';
import { Reconciliation } from '@/routes/Reconciliation';

export function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/monitoring" element={<Monitoring />} />
        <Route path="/reconciliation" element={<Reconciliation />} />
        <Route path="/cases" element={<Cases />} />
        <Route path="/cases/:caseId" element={<CaseDetail />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
