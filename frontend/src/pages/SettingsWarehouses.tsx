import PageHeader from "../components/PageHeader";
import Placeholder from "../components/Placeholder";

export default function SettingsWarehouses() {
  return (
    <>
      <PageHeader
        title="Warehouses"
        subtitle="Warehouses and the locations inside them."
        actions={
          <button type="button" className="btn-primary" disabled>
            New warehouse
          </button>
        }
      />
      <Placeholder note="Warehouse and location management lands in a later commit." />
    </>
  );
}
