// import { Request, Response, Router } from "express";
// import { getRedisClient } from "../clients";
// import { getPrismaClient } from "../lib/database";
// import { GetQuotesRequestSchema } from "../schemas";

// const router = Router();

// router.get("/random", async (req: Request, res: Response) => {
//   const prismaClient = getPrismaClient();
//   const quotes = await prismaClient.quote.findMany({
//     take: 10,
//   });

//   const randomIndex = Math.floor(Math.random() * quotes.length);
//   const randomQuote = quotes[randomIndex];

//   res.json({
//     success: true,
//     data: randomQuote,
//     timestamp: new Date().toISOString(),
//   });
// });

// router.get("/", async (req: Request, res: Response) => {
//   const parsed = GetQuotesRequestSchema.safeParse(req);

//   if (!parsed.success) {
//     res.status(400).json({ errors: parsed.error.format() });
//     return;
//   }

//   const { page, limit } = parsed.data.query;

//   const prismaClient = getPrismaClient();
//   const totalQuotes = await prismaClient.quote.count();

//   const skip = (page - 1) * limit;

//   const quotes = await prismaClient.quote.findMany({
//     skip,
//     take: limit,
//     orderBy: {
//       updatedAt: "desc",
//     },
//   });

//   const totalPages = Math.ceil(totalQuotes / limit);

//   res.json({
//     success: true,
//     data: quotes,
//     pagination: {
//       page,
//       limit,
//       total: totalQuotes,
//       totalPages,
//     },
//     timestamp: new Date().toISOString(),
//   });
// });

// router.get("/search", async (req: Request, res: Response) => {
//   const prismaClient = getPrismaClient();
//   const quotes = await prismaClient.quote.findMany();
//   const query = req.query.q as string;
//   const filteredQuotes = quotes.filter((q) => q.text.includes(query));
//   res.json({
//     success: true,
//     data: filteredQuotes,
//     count: filteredQuotes.length,
//     timestamp: new Date().toISOString(),
//   });
// });

// router.get("/:id", async (req: Request, res: Response) => {
//   const prismaClient = getPrismaClient();
//   const quote = await prismaClient.quote.findUnique({
//     where: {
//       id: req.params.id,
//     },
//   });

//   if (!quote) {
//     return res.status(404).json({
//       success: false,
//       error: "Quote not found",
//       timestamp: new Date().toISOString(),
//     });
//   }

//   res.json({
//     success: true,
//     data: quote,
//     timestamp: new Date().toISOString(),
//   });
// });

// router.delete("/:id", async (req: Request, res: Response) => {
//   const prismaClient = getPrismaClient();
//   const quote = await prismaClient.quote.delete({
//     where: {
//       id: req.params.id,
//     },
//   });

//   if (!quote) {
//     return res.status(404).json({
//       success: false,
//       error: "Quote not found",
//       timestamp: new Date().toISOString(),
//     });
//   }

//   // Emit event to Redis stream
//   await getRedisClient().xadd(
//     "feed",
//     "*",
//     "type",
//     "quote-deleted",
//     "data",
//     JSON.stringify({ quoteId: req.params.id, timestamp: new Date().toISOString() })
//   );

//   res.json({
//     success: true,
//     timestamp: new Date().toISOString(),
//   });
// });

// router.post("/", async (req: Request, res: Response) => {
//   const prismaClient = getPrismaClient();
//   const quote = await prismaClient.quote.create({
//     data: req.body,
//   });
//   // Emit event to Redis stream
//   await getRedisClient().xadd(
//     "feed",
//     "*",
//     "type",
//     "quote-created",
//     "data",
//     JSON.stringify({ quote, timestamp: new Date().toISOString() })
//   );

//   res.json({
//     success: true,
//     data: quote,
//   });
// });

// export default router;
