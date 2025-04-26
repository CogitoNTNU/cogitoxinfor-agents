
import { TestAction } from './components/TestActionsList';

declare global {
  interface Window {
    testActions: TestAction[];
    humanIntervention: boolean;
  }
}

export {};
