/** The words for what a report is about: "phone" → Phones, "earbuds" → Earbuds. */
export function productWords(product: string | undefined) {
  const one = (product || "product").trim()
  const many = one.endsWith("s") ? one : `${one}s`
  const title = many.charAt(0).toUpperCase() + many.slice(1)
  return { one, many, title }
}
