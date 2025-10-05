// import bcrypt from 'bcrypt';
// import { Request, Response, Router } from 'express';
// import jwt from 'jsonwebtoken';
// import type { StringValue } from 'ms';
// import { env } from '../../config';
// import { LoginRequestSchema } from '../schemas';
// import { zodParse } from '../utils';

// const router = Router();

// router.post('/login', async (req: Request, res: Response) => {
//   try {
//     const { username, password } = zodParse(LoginRequestSchema, req.body);

//     const prisma = getPrismaClient();

//     const user = await prisma.user.findUnique({
//       where: {
//         username,
//       },
//     });

//     let isValid = false;
//     if (user) {
//       const passwordHash = user.passwordHash;
//       isValid = await bcrypt.compare(password, passwordHash);
//     }

//     if (isValid) {
//       const token = jwt.sign(
//         {
//           userId: '1',
//           username: username,
//           role: 'user',
//         },
//         env.JWT_SECRET,
//         { expiresIn: env.JWT_EXPIRES_IN as StringValue }
//       );

//       // eslint-disable-next-line @typescript-eslint/no-unused-vars
//       const { passwordHash, createdAt, updatedAt, ...userData } = user!;

//       res.json({
//         token,
//         user: {
//           ...userData,
//           role: 'user',
//         },
//       });
//     } else {
//       res.status(401).json({ message: 'invalid credentials' });
//     }
//   } catch (error) {
//     console.log('Login failed', error);
//     res.status(400).json({ message: 'invalid request' });
//   }
// });

// router.get('/validate', async (req: Request, res: Response) => {
//   try {
//     const authHeader = req.headers.authorization;

//     if (!authHeader || !authHeader.startsWith('Bearer ')) {
//       return res.status(401).json({ message: 'No token provided' });
//     }

//     const token = authHeader.substring(7); // Remove 'Bearer ' prefix

//     // Verify JWT token
//     const decoded = jwt.verify(token, env.JWT_SECRET) as {
//       userId: string;
//       username: string;
//       role: string;
//     };

//     res.json({
//       id: decoded.userId,
//       username: decoded.username,
//       role: decoded.role,
//     });
//   } catch (error) {
//     console.log('Token validation failed', error);
//     res.status(401).json({ message: 'Invalid token' });
//   }
// });

// export default router;
