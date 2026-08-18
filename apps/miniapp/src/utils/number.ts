/**
 * 统一处理业务数值展示：去掉小数末尾无意义的 0，整数不显示小数部分。
 * 不使用 Number 转换，避免大数或高精度小数在展示前发生精度丢失。
 */
export function formatNumber(value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === "") return "";

  const text = String(value).trim();
  if (!/^[+-]?\d+(?:\.\d+)?$/.test(text)) return text;

  const [integerPart, fractionPart] = text.replace(/^\+/, "").split(".");
  const isNegative = integerPart.startsWith("-");
  const integerDigits = integerPart.replace(/^-/, "").replace(/^0+(?=\d)/, "") || "0";
  const fractionDigits = fractionPart?.replace(/0+$/, "") || "";

  if (!fractionDigits) return integerDigits === "0" ? "0" : `${isNegative ? "-" : ""}${integerDigits}`;
  return `${isNegative ? "-" : ""}${integerDigits}.${fractionDigits}`;
}
