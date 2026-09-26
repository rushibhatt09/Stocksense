import PageHeader from "../components/PageHeader";
import Placeholder from "../components/Placeholder";

export default function Products() {
  return (
    <>
      <PageHeader
        title="Products"
        subtitle="Every product, its SKU and stock on hand."
        actions={
          <button type="button" className="btn-primary" disabled>
            New product
          </button>
        }
      />
      <Placeholder note="The product table, SKU search and category filters land in a later commit." />
    </>
  );
}
