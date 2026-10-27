using System;
public class RevisionFixture {
 public static int Main(string[] args) {
   int n=0; if(args.Length>0 && !Int32.TryParse(args[0],out n)) return 2;
   Console.WriteLine("X_SENTINEL_BENIGN_FIXTURE:"+(n*n+7)); return 0;
 }
}