export function setNestedValue(obj: any, path: string[], value: any): any {
  if (path.length === 0) return value
  
  const [key, ...rest] = path
  const current = obj[key]
  
  if (rest.length === 0) {
    return { ...obj, [key]: value }
  }
  
  return { 
    ...obj, 
    [key]: setNestedValue(current || {}, rest, value) 
  }
}
