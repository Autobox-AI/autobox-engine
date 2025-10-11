import { Worker as BullMQWorker, Job } from 'bullmq';
import { logger, redisConfig, simulationsQueue } from '../../config';

export const createExecutor = async (simulationId: string) => {
  const dispatch = async (): Promise<void> => {
    await simulationsQueue.add(
      'simulation',
      {
        simulationId,
        timeoutSeconds: 10,
      },
      { jobId: simulationId }
    );
  };

  const run = async (job: Job): Promise<{ success: boolean; message: string }> => {
    logger.info(`Processing job: ${job.id}`);
    // const { timeoutSeconds } = job.data;
    logger.info(
      // `Running simulation: ${this.simulationId} with parameters: ${JSON.stringify(job.data)}`
      `Running simulation: X with parameters: ${JSON.stringify(job.data)}`
    );
    return { success: true, message: 'Simulation completed' };
  };

  const createJobWorker = async (): Promise<BullMQWorker> => {
    return new BullMQWorker(
      'simulation',
      async (job) => {
        await run(job);
      },
      {
        connection: redisConfig,
      }
    );
  };

  return {
    dispatch,
    createJobWorker,
  };
};

// export class Run {
//   id: string
//   simulationId: string
//   name: string
//   description: string | null
//   status: RunStatus
//   startedAt: string
//   finishedAt?: string
//   abortedAt?: string
//   summary?: string
//   progress: number
//   workers: Worker[]
//   orchestrator: Orchestrator
//   planner: Planner
//   reporter: Reporter
//   evaluator: Evaluator
//   task: string
//   traces?: string[]
//   worker: BullMQWorker

//   constructor({
//     id,
//     simulationId,
//     name,
//     description,
//     status,
//     startedAt,
//     finishedAt,
//     abortedAt,
//     summary,
//     progress,
//     workers,
//     orchestrator,
//     planner,
//     reporter,
//     evaluator,
//     task,
//     traces,
//   }: RunParams) {
//     this.id = id
//     this.simulationId = simulationId
//     this.name = name
//     this.description = description
//     this.status = status
//     this.startedAt = startedAt
//     this.finishedAt = finishedAt
//     this.abortedAt = abortedAt
//     this.summary = summary
//     this.progress = progress
//     this.workers = workers
//     this.orchestrator = orchestrator
//     this.planner = planner
//     this.reporter = reporter
//     this.evaluator = evaluator
//     this.task = task
//     this.traces = traces
//     this.worker = new BullMQWorker(
//       `run_${this.id}`,
//       async (job) => {
//         await this.run(job)
//       },
//       {
//         connection: redisConfig,
//       }
//     )
//   }

//   private async cleanup(): Promise<void> {
//     try {
//       await this.orchestrator.shutdown()
//       await this.worker.close()
//     } catch (error) {
//       logger.error('Error during simulation cleanup:', error)
//     }
//   }

//   async run(job: Job): Promise<{ success: boolean; message: string }> {
//     logger.info(`Processing job: ${job.id}`)
//     const { timeoutSeconds } = job.data
//     logger.info(
//       `Running simulation: ${this.simulationId} with parameters: ${JSON.stringify(job.data)}`
//     )
//     const startTime = Date.now()
//     try {
//       const timeoutController = new AbortController()
//       const timeoutPromise = new Promise<never>((_, reject) => {
//         const timeoutId = setTimeout(() => {
//           reject(
//             new Error(`Simulation ${this.simulationId} timeout after ${timeoutSeconds} seconds`)
//           )
//         }, timeoutSeconds * 1000)

//         timeoutController.signal.addEventListener('abort', () => {
//           clearTimeout(timeoutId)
//         })
//       })

//       try {
//         await Promise.race([
//           this.orchestrator.runUntilCompletion().then((result) => {
//             timeoutController.abort()
//             return result
//           }),
//           timeoutPromise,
//         ])

//         const timeDuration = formatTimeDuration(startTime)
//         logger.info(
//           `Simulation ${this.simulationId} completed for job: ${job.id} in ${timeDuration}`
//         )

//         await updateRun({
//           runId: this.id,
//           progress: 100,
//           status: 'completed',
//           finishedAt: new Date().toISOString(),
//         })

//         return {
//           success: true,
//           message: `Simulation ${this.simulationId} finished successfully in ${timeDuration}`,
//         }
//       } catch (error) {
//         throw error
//       } finally {
//         await this.cleanup()
//       }
//     } catch (error: unknown) {
//       const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
//       logger.error(`Simulation failed: ${errorMessage}`)
//       return { success: false, message: errorMessage }
//     }
//   }

//   async shutdown(): Promise<void> {
//     await this.cleanup()
//   }
// }
