import PageHeader from "../components/PageHeader";
import Placeholder from "../components/Placeholder";

export default function Transfers() {
  return (
    <>
      <PageHeader
        title="Internal Transfers"
        subtitle="Move stock between locations inside the company."
        actions={
          <button type="button" className="btn-primary" disabled>
            New transfer
          </button>
        }
      />
      <Placeholder note="The transfer list and form land in a later commit." />
    </>
  );
}
