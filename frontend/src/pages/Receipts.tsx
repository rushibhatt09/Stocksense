import PageHeader from "../components/PageHeader";
import Placeholder from "../components/Placeholder";

export default function Receipts() {
  return (
    <>
      <PageHeader
        title="Receipts"
        subtitle="Incoming stock from vendors."
        actions={
          <button type="button" className="btn-primary" disabled>
            New receipt
          </button>
        }
      />
      <Placeholder note="The receipt list and form land in a later commit." />
    </>
  );
}
