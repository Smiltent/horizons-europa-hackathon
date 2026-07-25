const TOTAL_LEN = 12

export function createIdGenerator(prefix: string) {
    const numLen = TOTAL_LEN - prefix.length
    const max = 10 ** numLen - 1
    let counter = 0

    return () => {
        counter = (counter % max) + 1
        return prefix + String(counter).padStart(numLen, "0")
    }
}
