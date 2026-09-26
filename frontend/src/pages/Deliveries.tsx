import PageHeader from "../components/PageHeader";
import Placeholder from "../components/Placeholder";

export default function Deliveries() {
  return (
    <>
      <PageHeader
        title="Delivery Orders"
        subtitle="Outgoing stock to customers."
        actions={
          <button type="button" className="btn-primary" disabled>
            New delivery order
          </button>
        }
      />
      <Placeholder note="The delivery list and the pick, pack, validate flow land in a later commit." />
    </>
  );
}
