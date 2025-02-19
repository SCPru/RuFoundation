import { useRef, useCallback } from 'react';

export default function useConstCallback<T extends (...args: any[]) => any>(callback: T) {
    const ref = useRef<T>(callback)
    ref.current = callback
    return useCallback((...args: Parameters<T>) => ref.current(...args), [])
}