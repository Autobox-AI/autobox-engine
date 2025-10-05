// import { Request, Response, Router } from 'express';
// import { clearInterval, setInterval } from 'timers';
// import { setTimeout } from 'timers/promises';
// import { createStreamRedisClient, getRedisClient } from '../clients';
// import { getPrismaClient } from '../lib';
// import { authenticate } from '../middlewares';
// import { FEED_TYPES, FeedEvent, PostRandomQuoteFeedRequestSchema } from '../schemas';
// import { zodParse } from '../utils';

// const router = Router();

// router.get('/stream', async (req: Request, res: Response) => {
//   res.setHeader('Content-Type', 'text/event-stream');
//   res.setHeader('Cache-Control', 'no-cache');
//   res.setHeader('Connection', 'keep-alive');
//   res.setHeader('Access-Control-Allow-Origin', '*');

//   // Send initial connection success
//   res.write(':connected\n\n');

//   // Create a dedicated Redis client for this SSE connection
//   // const streamReader = new Redis(redisConfig);
//   const streamReader = createStreamRedisClient();

//   // EventSource API sends last-event-id as query param on reconnection
//   let lastId = (req.query.lastEventId as string) || (req.headers['last-event-id'] as string) || '$';
//   let isConnected = true;

//   console.log(`New SSE client connected. Starting from ID: ${lastId}`);

//   // Handle client disconnect
//   req.on('close', () => {
//     console.log('Client disconnected from stream');
//     isConnected = false;
//     streamReader.disconnect();
//   });

//   // Send heartbeat every 30 seconds to keep connection alive
//   const heartbeat = setInterval(() => {
//     if (!isConnected) {
//       clearInterval(heartbeat);
//       return;
//     }
//     res.write(':heartbeat\n\n');
//   }, 30000);

//   // Read from Redis Stream with non-blocking polling
//   const listenToStream = async () => {
//     while (isConnected) {
//       try {
//         // console.log(`SSE client reading from ID: ${lastId}`);

//         // Use XREAD with a timeout instead of blocking indefinitely
//         // This allows multiple clients to read the same messages
//         const messages = await streamReader.xread(
//           'COUNT',
//           10,
//           'BLOCK',
//           1000, // Block for 1 second max
//           'STREAMS',
//           'feed',
//           lastId
//         );

//         if (!isConnected) break;

//         if (messages && messages.length > 0) {
//           for (const stream of messages) {
//             const [streamName, streamMessages] = stream;
//             console.log(
//               `SSE client processing ${streamMessages.length} messages from stream: ${streamName}`
//             );

//             for (const [messageId, fields] of streamMessages) {
//               // Update lastId to this message ID for next read
//               lastId = messageId;

//               // Parse fields into an object
//               const fieldObj: Record<string, string> = {};
//               for (let i = 0; i < fields.length; i += 2) {
//                 fieldObj[fields[i]] = fields[i + 1];
//               }

//               console.log('SSE sending to client:', fieldObj);

//               // Send SSE event
//               const eventType = fieldObj.type || 'message';
//               const eventData = fieldObj.data || JSON.stringify(fieldObj);

//               res.write(`id: ${messageId}
// `);
//               res.write(`event: ${eventType}
// `);
//               res.write(`data: ${eventData}

// `);
//             }
//           }
//         }
//       } catch (error) {
//         if (!isConnected) break;

//         // Check if it's just a timeout (normal for XREAD BLOCK)
//         if (error instanceof Error && error.message.includes('timeout')) {
//           // This is normal - just continue polling
//           continue;
//         }

//         console.error('Error in stream listener:', error);
//         // Wait a bit before retrying
//         await setTimeout(1000);
//       }
//     }

//     clearInterval(heartbeat);
//     res.end();
//   };

//   // Start listening to the stream
//   listenToStream();
// });

// router.post('/random', authenticate, async (req: Request, res: Response) => {
//   console.log('POST /random received:', req.body);

//   let quote;

//   const redisClient = getRedisClient();
//   const prismaClient = getPrismaClient();

//   try {
//     const request = zodParse(PostRandomQuoteFeedRequestSchema, req.body);
//     quote = request.quote;
//   } catch (error) {
//     console.error('Zod validation error:', error);
//     return res.status(400).json({ success: false, error: 'Invalid request body' });
//   }

//   try {
//     // if (redisClient.status !== "ready") {
//     //   console.error("Redis stream client is not ready. Status:", redisClient.status);

//     //   try {
//     //     await redisClient.ping();
//     //     console.log("Redis ping successful");
//     //   } catch (pingError) {
//     //     console.error("Redis ping failed:", pingError);
//     //     return res.status(503).json({
//     //       success: false,
//     //       error: "Redis connection not ready",
//     //       status: redisClient.status,
//     //     });
//     //   }
//     // }

//     const feedEvent: FeedEvent = {
//       type: FEED_TYPES.RANDOM_QUOTE,
//       metadata: {
//         username: req.user!.username,
//         timestamp: new Date().toISOString(),
//       },
//       data: {
//         quote,
//       },
//     };

//     console.log('Attempting xadd with data:', feedEvent);

//     const [, messageId] = await Promise.all([
//       prismaClient.feed.create({
//         data: {
//           type: feedEvent.type,
//           data: feedEvent.data,
//           userId: req.user!.userId,
//           createdAt: feedEvent.metadata.timestamp,
//         },
//       }),
//       redisClient.xadd('feed', '*', 'type', feedEvent.type, 'data', JSON.stringify(feedEvent)),
//     ]);

//     console.log('Message added to stream with ID:', messageId);

//     // Optionally verify the message was added (remove if not needed for performance)
//     try {
//       const checkMessages = await redisClient.xrange('feed', '-', '+', 'COUNT', 5);
//       console.log(`Stream now has ${checkMessages.length} recent messages`);
//     } catch (verifyError) {
//       console.warn('Could not verify stream messages:', verifyError);
//       // Don't fail the request if verification fails
//     }

//     res.json({
//       success: true,
//       message: 'Quote added to stream',
//       messageId,
//       timestamp: feedEvent.metadata.timestamp,
//     });
//   } catch (error: any) {
//     console.error('Error adding to stream:', error);
//     console.error('Error details:', {
//       message: error.message,
//       code: error.code,
//       stack: error.stack,
//     });

//     // Return more detailed error information
//     res.status(500).json({
//       success: false,
//       error: error.message || 'Failed to add to stream',
//       details: {
//         code: error.code,
//         redisStatus: redisClient.status,
//       },
//     });
//   }
// });

// // Endpoint to clear all feed data
// router.delete('/clear', async (req: Request, res: Response) => {
//   const redisClient = getRedisClient();

//   try {
//     console.log('Clearing all feed data from Redis stream...');

//     // Delete the entire stream
//     await redisClient.del('feed');

//     // Recreate the stream with an initial message
//     await redisClient.xadd(
//       'feed',
//       '*',
//       'type',
//       'system',
//       'data',
//       JSON.stringify({ message: 'Feed cleared', timestamp: new Date().toISOString() })
//     );

//     console.log('Feed cleared and reinitialized');

//     res.json({
//       success: true,
//       message: 'All feed data has been cleared',
//       timestamp: new Date().toISOString(),
//     });
//   } catch (error) {
//     console.error('Error clearing feed:', error);
//     res.status(500).json({
//       success: false,
//       error: 'Failed to clear feed data',
//       details: error instanceof Error ? error.message : String(error),
//     });
//   }
// });

// export default router;
