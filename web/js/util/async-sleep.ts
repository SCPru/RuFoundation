export default function sleep(amt: number): Promise<void> {
  return new Promise(resolve => {
    setTimeout(resolve, amt)
  })
}
