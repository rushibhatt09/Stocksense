import PageHeader from "../components/PageHeader";
import Placeholder from "../components/Placeholder";

export default function Adjustments() {
  return (
    <>
      <PageHeader
        title="Inventory Adjustment"
        subtitle="Correct recorded stock against a physical count."
        actions={
          <button type="button" className="btn-primary" disabled>
            New adjustment
          </button>
        }
      />
      <Placeholder note="The counted-versus-recorded form lands in a later commit." />
    </>
  );
}
